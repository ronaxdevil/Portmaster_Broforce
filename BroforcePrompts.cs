// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: 2026 Ronax
using Mono.Cecil;
using Mono.Cecil.Cil;

namespace AsmPatch;

sealed class BroforcePrompts : Patch
{
    public override string Name => "broforce-prompts";
    public override string Summary => "Display Nintendo face-button letters in Broforce's controller bindings";
    public override Kind Kind => Kind.Prompts;
    public override bool OptIn => true;

    public override Result Run(Game game, bool apply)
    {
        var assembly = game.Load("Assembly-CSharp");
        var module = assembly?.MainModule;
        var menu = module?.GetType("KeyBindingMenu");
        var binding = menu?.Methods.SingleOrDefault(m => m.Name == "GetJoystickBind" && m.HasBody);
        var lookup = binding?.Body.Instructions.SingleOrDefault(i =>
            i.OpCode == OpCodes.Callvirt && i.Operand is MethodReference call &&
            call.DeclaringType.FullName == "Rewired.ActionElementMap" && call.Name == "get_elementIdentifierName");
        if (lookup == null)
            return Result.Failed("Broforce's controller binding label lookup differs from the supported build");

        const string detail = "Assembly-CSharp.dll: Nintendo face-button labels in Controls, preserving physical bindings";
        if (lookup.Next?.Operand is MethodReference existing && existing.Name == "PortMasterFaceButtonLabel" &&
            existing.DeclaringType.FullName == menu.FullName)
            return new Result { Outcome = Outcome.AlreadyApplied, Details = { detail } };

        if (apply)
        {
            var helper = AddLabelHelper(module, menu);
            binding.Body.GetILProcessor().InsertAfter(lookup, Instruction.Create(OpCodes.Call, helper));
            game.MarkChanged(assembly);
        }
        return new Result { Outcome = Outcome.Applied, Details = { detail } };
    }

    static MethodDefinition AddLabelHelper(ModuleDefinition module, TypeDefinition menu)
    {
        var types = module.TypeSystem;
        var environment = new TypeReference("System", "Environment", module, types.CoreLibrary);
        var getEnvironment = new MethodReference("GetEnvironmentVariable", types.String, environment);
        getEnvironment.Parameters.Add(new ParameterDefinition(types.String));
        var equals = new MethodReference("op_Equality", types.Boolean, types.String);
        equals.Parameters.Add(new ParameterDefinition(types.String));
        equals.Parameters.Add(new ParameterDefinition(types.String));

        var method = new MethodDefinition("PortMasterFaceButtonLabel", MethodAttributes.Private |
            MethodAttributes.Static | MethodAttributes.HideBySig, types.String);
        method.Parameters.Add(new ParameterDefinition("label", ParameterAttributes.None, types.String));
        menu.Methods.Add(method);
        var il = method.Body.GetILProcessor();
        var original = il.Create(OpCodes.Ldarg_0);
        il.Emit(OpCodes.Ldstr, "BROFORCE_PROMPTS");
        il.Emit(OpCodes.Call, getEnvironment);
        il.Emit(OpCodes.Ldstr, "nintendo");
        il.Emit(OpCodes.Call, equals);
        il.Emit(OpCodes.Brfalse, original);

        foreach (var (xbox, nintendo) in new[] { ("A", "B"), ("B", "A"), ("X", "Y"), ("Y", "X") })
        {
            var next = il.Create(OpCodes.Nop);
            il.Emit(OpCodes.Ldarg_0);
            il.Emit(OpCodes.Ldstr, xbox);
            il.Emit(OpCodes.Call, equals);
            il.Emit(OpCodes.Brfalse, next);
            il.Emit(OpCodes.Ldstr, nintendo);
            il.Emit(OpCodes.Ret);
            il.Append(next);
        }
        il.Append(original);
        il.Emit(OpCodes.Ret);
        return method;
    }
}
