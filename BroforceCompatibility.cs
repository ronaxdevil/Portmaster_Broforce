// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: 2026 Ronax
using Mono.Cecil;
using Mono.Cecil.Cil;

namespace AsmPatch;

sealed class BroforceCompatibility : Patch
{
    public override string Name => "broforce-compatibility";
    public override string Summary => "Use offline Steam results, initialize Odin on ARM, and handle missing launch arguments";
    public override bool OptIn => true;

    public override Result Run(Game game, bool apply)
    {
        var steam = game.Load("Assembly-CSharp-firstpass");
        var odin = game.Load("Sisus.OdinSerializer");
        var main = game.Load("Assembly-CSharp");
        var api = steam?.MainModule.GetType("Steamworks.SteamAPI");
        var initializer = odin?.MainModule.GetType("Sisus.OdinSerializer.UnitySerializationInitializer");
        var intro = main?.MainModule.GetType("IntroController");
        if (api == null || initializer == null || intro == null)
            return Result.Failed("Broforce's Steamworks, Odin, or intro code is missing");

        var offline = new[]
        {
            (Wrapper: "IsSteamRunning", Native: "SteamAPI_IsSteamRunning"),
            (Wrapper: "Init", Native: "SteamAPI_InitSafe"),
            (Wrapper: "RestartAppIfNecessary", Native: "SteamAPI_RestartAppIfNecessary"),
        };
        var methods = new List<MethodDefinition>();
        foreach (var target in offline)
        {
            var method = api.Methods.SingleOrDefault(m => m.Name == target.Wrapper && m.HasBody &&
                m.ReturnType.MetadataType == MetadataType.Boolean &&
                m.Body.Instructions.Any(i => i.Operand is MethodReference call &&
                    call.DeclaringType.FullName == "Steamworks.NativeMethods" && call.Name == target.Native));
            if (method == null)
                return Result.Failed($"The expected SteamAPI.{target.Wrapper} wrapper is missing");
            methods.Add(method);
        }

        var init = initializer.Methods.SingleOrDefault(m => m.Name == "Initialize" && m.HasBody);
        if (init == null)
            return Result.Failed("Odin's initialization method is missing");
        var code = init.Body.Instructions;
        var java = code.SingleOrDefault(i => i.OpCode == OpCodes.Ldstr && Equals(i.Operand, "java.lang.System"));
        var arch = code.SingleOrDefault(i => i.OpCode == OpCodes.Call && i.Operand is MethodReference call &&
            call.DeclaringType.FullName == "Sisus.OdinSerializer.ArchitectureInfo" && call.Name == "SetIsOnAndroid");
        if (java?.Next?.Operand is not MethodReference constructor ||
            constructor.DeclaringType.FullName != "UnityEngine.AndroidJavaClass" ||
            java.Next.Next?.OpCode != OpCodes.Stloc_1 || arch?.Previous?.OpCode != OpCodes.Ldloc_2 ||
            code.IndexOf(arch) - code.IndexOf(java) != 14 ||
            !code.Any(i => i.OpCode == OpCodes.Ldstr && Equals(i.Operand, "os.arch")))
            return Result.Failed("Odin's Java architecture lookup differs from the supported build");

        var argsMethod = intro.Methods.SingleOrDefault(m => m.Name == "ProcessCommandLineArguments" && m.HasBody);
        var getArgs = argsMethod?.Body.Instructions[0];
        if (getArgs?.Operand is not MethodReference get || get.Name != "GetCommandLineArgs" ||
            get.DeclaringType.FullName != "System.Environment" || getArgs.Next?.OpCode != OpCodes.Stloc_0)
            return Result.Failed("The intro's command-line argument handling differs from the supported build");

        if (apply)
        {
            foreach (var method in methods)
            {
                method.Body = new MethodBody(method);
                var il = method.Body.GetILProcessor();
                il.Emit(OpCodes.Ldc_I4_0);
                il.Emit(OpCodes.Ret);
            }
            game.MarkChanged(steam);

            // Keep the original lock, exception handlers, and architecture callback. A null
            // Java object skips its Dispose handler. "armv7" selects safe bytewise access.
            java.OpCode = OpCodes.Ldnull;
            java.Operand = null;
            java.Next.OpCode = OpCodes.Nop;
            java.Next.Operand = null;
            for (var i = java.Next.Next.Next; i != arch.Previous; i = i.Next)
            {
                i.OpCode = OpCodes.Nop;
                i.Operand = null;
            }
            arch.Previous.OpCode = OpCodes.Ldstr;
            arch.Previous.Operand = "armv7";
            game.MarkChanged(odin);

            // This Mono player can return null instead of the empty argument list.
            var argIL = argsMethod.Body.GetILProcessor();
            var store = getArgs.Next;
            argIL.InsertBefore(store, argIL.Create(OpCodes.Dup));
            argIL.InsertBefore(store, argIL.Create(OpCodes.Brtrue_S, store));
            argIL.InsertBefore(store, argIL.Create(OpCodes.Pop));
            argIL.InsertBefore(store, argIL.Create(OpCodes.Ldc_I4_0));
            argIL.InsertBefore(store, argIL.Create(OpCodes.Newarr, main.MainModule.TypeSystem.String));
            game.MarkChanged(main);
        }

        var result = new Result { Outcome = Outcome.Applied };
        result.Details.Add("Assembly-CSharp-firstpass.dll: Steam unavailable and initialization returns false");
        result.Details.Add("Sisus.OdinSerializer.dll: ARM alignment initialized without Java reflection");
        result.Details.Add("Assembly-CSharp.dll: intro treats null command-line arguments as an empty array");
        return result;
    }
}
